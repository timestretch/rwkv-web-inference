import React from "react"
import { useForm, Controller } from "react-hook-form"
import TextField from "@mui/material/TextField"
import Button from "@mui/material/Button"
import Grid from "@mui/material/Grid"
import Card from "@mui/material/Card"
import CardContent from "@mui/material/CardContent"
import Typography from "@mui/material/CardContent"

function LoginForm() {
	const {
		register,
		control,
		handleSubmit,
		watch,
		formState: { errors }
	} = useForm()

	const onSubmit = data => console.log(data)
	console.log(watch("email")) // watch input value by passing the name of it
	console.log(watch("password")) // watch input value by passing the name of it

	const [email, setEmail] = React.useState("")
	const [password, setPassword] = React.useState("")
	const [error, setError] = React.useState(null)

	return (
		<Card sx={{ m: 4 }}>
			<CardContent>
				<form onSubmit={handleSubmit(onSubmit)}>
					<Grid container spacing={2}>
						<Grid item sm={12}>
							<Controller
								control={control}
								name="email"
								render={({ field }) => (
									<TextField fullWidth type="email" label="Email" {...field} />
								)}
							/>
						</Grid>
						<Grid item sm={12}>
							<Controller
								name="password"
								control={control}
								render={({ field }) => (
									<TextField
										fullWidth
										label="Password"
										type="password"
										{...field}
									/>
								)}
							/>
						</Grid>
					</Grid>
					{error && <p>{error}</p>}
					<Button type="submit" variant="contained" sx={{ mt: 2 }}>
						Log in
					</Button>
				</form>
			</CardContent>
		</Card>
	)
}

export default LoginForm
