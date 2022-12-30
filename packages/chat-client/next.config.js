module.exports = () => {

  const headers = () => {
    return [
      {
        source: '/',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: 'http://localhost:8080/api',
          },
        ],
      },
    ]
  };

  const rewrites = () => {
    return [
      {
        source: "/api",
        destination: "http://127.0.0.1:8080/api",
      },
    ];
  };
  
  
  return {
    experimental: {
    	proxyTimeout: 120_000
    },
    rewrites,
    headers,
  };
};
