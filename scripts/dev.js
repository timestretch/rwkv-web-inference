const concurrently = require('concurrently');
const path = require('node:path');

const { result } = concurrently(
  [
    {
      command: 'npm run dev',
      name: 'chat client',
      cwd: path.resolve(__dirname, '../packages/chat-client'),
    },
    {
      command: "flask run -h 0.0.0.0 -p 8080",
      name: 'chat server',
      cwd: path.resolve(__dirname, '../server'),
    }
  ],
  {
    prefix: 'name',
    killOthers: ['failure', 'success'],
  }
);

result.catch((error) => {
  console.error(error);
  process.exit(1);
})
