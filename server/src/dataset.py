########################################################################################################
# The RWKV Language Model - https://github.com/BlinkDL/RWKV-LM
########################################################################################################

import json, math, random
import numpy as np
import torch
from torch.utils.data import Dataset
from pytorch_lightning.utilities import rank_zero_info
from .binidx import MMapIndexedDataset
from .utils import MaybeIsPrime


class MyDataset(Dataset):
    def __init__(self, args):
        self.args = args

        if args.data_type == "binidx":
            self.data = MMapIndexedDataset(args.data_file)
            self.vocab_size = args.vocab_size
            print("Current vocab size =", self.vocab_size, "(make sure it's correct)")
            self.data_size = len(self.data._bin_buffer) // 2
            print(f"Data has {self.data_size} tokens.")

            if args.my_pile_stage > 0:
                assert self.data_size == 332115325534 and self.vocab_size == 50277
                self.samples_per_epoch = args.epoch_steps * args.real_bsz
                assert self.samples_per_epoch == 40320
                print(f"########## Pile 20b-tokenized stage {args.my_pile_stage} ##########")
                dataset_slot = self.data_size // args.ctx_len
                assert MaybeIsPrime(args.magic_prime)
                assert args.magic_prime % 3 == 2
                assert args.magic_prime / dataset_slot > 0.999999 and args.magic_prime / dataset_slot <= 1
        elif args.data_type == "numpy":
            self.data = np.load(args.data_file).astype("int")
            self.vocab_size = args.vocab_size
            print("Current vocab size =", self.vocab_size, "(make sure it's correct)")
            self.data_size = len(self.data)
            print(f"Data has {self.data_size} tokens.")
        elif args.data_type == "uint16":
            self.data = np.fromfile(args.data_file, dtype=np.uint16).astype("int32").reshape(-1, args.my_sample_len)
            self.vocab_size = args.vocab_size
            print("Current vocab size =", self.vocab_size, "(make sure it's correct)")
            self.data_size = self.data.shape[0]
            print(f"Data has {self.data_size} samples.")
        elif args.data_type == "wds_img":
            self.vocab_size = -1
            self.data_size = -1
            self.data = None
            self.error_count = 0
        else:
            if args.data_type == "dummy":
                print("Building dummy data...")
                self.data = ""
                for i in range(100000):
                    aa = (i) % 10000
                    bb = (i * i) % 10000
                    cc = aa + bb
                    self.data += f".{aa}+{bb}={cc}."
            else:
                self.data = open(args.data_file, "r", encoding=args.data_type).read()
            print("Building token list...")
            unique = sorted(list(set(self.data)))
            self.vocab_size = len(unique)
            # print()
            # for u in unique:
            #     print(u, end=' ')
            # print('\n\n')
            xx = 0
            xxObj = {}
            for u in unique:
                xxObj[xx] = u
                xx += 1
            with open(f"{args.proj_dir}/vocab.json", "w", encoding="utf-16le") as vocab_file:
                vocab_file.write(json.dumps(xxObj, ensure_ascii=False))
            self.data_size = len(self.data)
            print("Data has %d tokens, %d vocab size." % (self.data_size, self.vocab_size))
            self.stoi = {ch: i for i, ch in enumerate(unique)}
            self.itos = {i: ch for i, ch in enumerate(unique)}

    def __len__(self):
        return self.args.epoch_steps * self.args.micro_bsz

    def __getitem__(self, idx):
        args = self.args
        rank = self.global_rank
        epoch = self.real_epoch
        world_size = self.world_size
        # print(f"epoch {epoch} idx {idx} rank {rank}/{world_size}")

        if args.data_type == "wds_img":
            def init_wds(self, bias=0):
                def identity(x):
                    return x            
                import webdataset as wds
                import torchvision.transforms as transforms
                # img_transform = transforms.Compose(
                #     [transforms.CenterCrop(256)]
                # )
                img_transform = transforms.Compose([
                    transforms.CenterCrop(512),
                    transforms.Resize((args.my_img_size))
                ])
                self.data_raw = wds.WebDataset(args.data_file, resampled=True).shuffle(10000, initial=1000, rng=random.Random(epoch*100000+rank+bias*1e9)).decode("torchrgb").to_tuple("jpg", "json", "txt").map_tuple(img_transform, identity, identity)
                for pp in self.data_raw.pipeline:
                    if 'Resampled' in str(pp):
                        pp.deterministic = True
                        def worker_seed():
                            return rank*100000+epoch+bias*1e9
                        pp.worker_seed = worker_seed
                self.data = iter(self.data_raw)
                # print(f"WebDataset loaded for rank {rank} epoch {epoch}")
            if self.data == None:
                init_wds(self)
            trial = 0
            while trial < 10:
                try:
                    dd = next(self.data) # jpg, json, txt
                    break
                except:
                    print(f'[dataloader error - epoch {epoch} rank {rank} - trying a new shuffle]')
                    self.error_count += 1
                    init_wds(self, self.error_count)
                    trial += 1
                    pass
            # print(f"epoch {epoch} idx {idx} rank {rank}/{world_size} {dd[2]}")
            # with open(f"sample_{rank}.txt", "a", encoding="utf-8") as tmp:
            #     tmp.write(f"epoch {epoch} idx {idx} rank {rank}/{world_size} {int(dd[1]['key'])}\n")
            return dd[0], dd[2]
        else:
            if args.data_type == "uint16":
                i = np.random.randint(0, self.data_size-1)
                dix = self.data[i]
                x = torch.tensor(dix[:-1], dtype=torch.long)
                y = torch.tensor(dix[1:], dtype=torch.long)
            else:
                ctx_len = args.ctx_len
                req_len = ctx_len + 1

                if args.my_pile_stage > 0:
                    ii = 1 + epoch * self.samples_per_epoch + (idx * world_size) + rank
                    factor = (math.sqrt(5) - 1) / 2
                    factor = int(args.magic_prime * factor)
                    i = ((factor * ii * ii * ii) % args.magic_prime) * ctx_len
                    i = i + args.my_pile_shift
                    # print(f"epoch {epoch} idx {idx} rank {rank}/{world_size} ii {ii} pos {round(i / self.data_size, 3)}")
                else:
                    # cheat: pick a random spot in dataset
                    i = np.random.randint(0, self.data_size - req_len)

                if args.data_type == "binidx":
                    dix = self.data.get(idx=0, offset=i, length=req_len).astype(int)
                elif args.data_type == "numpy":
                    dix = self.data[i : i + req_len]
                else:
                    dix = [self.stoi[s] for s in self.data[i : i + req_len]]

                x = torch.tensor(dix[:-1], dtype=torch.long)
                y = torch.tensor(dix[1:], dtype=torch.long)
            return x, y
