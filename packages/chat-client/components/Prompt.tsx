import React from "react"
import { useForm, Controller } from "react-hook-form"
import TextField from "@mui/material/TextField"
import Button from "@mui/material/Button"
import Grid from "@mui/material/Grid"
import Card from "@mui/material/Card"
import CardContent from "@mui/material/CardContent"
import Typography from "@mui/material/CardContent"
import TextareaAutosize from "@mui/base/TextareaAutosize"
import Alert from "@mui/material/Alert"
import Stack from "@mui/material/Stack"

function LoginForm() {
	const {
		setValue,
		register,
		control,
		handleSubmit,
		watch,
		formState: { errors }
	} = useForm()

	const [submitting, setSubmitting] = React.useState(false)
	const [prompt, setPrompt] = React.useState("")
	const [error, setError] = React.useState(null)

	// 	console.log(watch("prompt")) // watch input value by passing the name of it

	const onSubmit = async formData => {
		setSubmitting(true)
		setError(null)
			
		console.log(formData)

		const query = {
			prompt: formData["prompt"],
			max_length: 10,
			stop: null
		}

		const response = await window.fetch("/api", {
			// learn more about this API here: https://graphql-pokemon2.vercel.app/
			method: "POST",
			headers: {
				"content-type": "application/json;charset=UTF-8"
			},
			body: JSON.stringify(query)
		})

		const json = await response.json()

		if (response.ok) {
			setSubmitting(false)
			setValue("prompt", json["prompt"] + json["completion"])
		} else {
			const errorString = "Response Status: " + response.status
			setError(errorString)
			const error = new Error(errorString)
			setSubmitting(false)
			return Promise.reject(error)
		}
	}

	return (
		<Card sx={{ m: 4 }}>
			<CardContent>
				<form onSubmit={handleSubmit(onSubmit)}>
					<Grid container spacing={2}>
						<Grid item sm={12}>
							<Typography>Enter your RWKV prompt here:</Typography>
						</Grid>
						<Grid item sm={12}>
							<Controller
								control={control}
								name="prompt"
								render={({ field }) => (
									<Stack
										direction="column"
										justifyContent="center"
										alignItems="stretch"
										spacing={2}
									>
										<TextareaAutosize
											minRows={12}
											disabled={submitting}
											{...field}
										/>
									</Stack>
								)}
							/>
						</Grid>
					</Grid>
					{error && (
						<Alert severity="error" sx={{ mt: 2 }}>
							{error}
						</Alert>
					)}
					<Button
						type="submit"
						variant="contained"
						sx={{ mt: 2 }}
						disabled={submitting}
					>
						Submit
					</Button>
				</form>
			</CardContent>
		</Card>
	)
}

export default LoginForm