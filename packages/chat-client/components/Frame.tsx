import React from 'react';

function Frame({children}) {
	return (
		<html>
			<head>
			</head>
			<body>
				{children}
			</body>
		</html>
	);
}

export default Frame;
