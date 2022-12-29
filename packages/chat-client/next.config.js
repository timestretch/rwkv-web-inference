module.exports = () => {
  const rewrites = () => {
    return [
      {
        source: "/api",
        destination: "http://127.0.0.1:8080",
      },
    ];
  };
  return {
    rewrites,
  };
};
