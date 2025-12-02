const reportWebVitals = onPerfEntry => {
  // ↑ This function accepts a callback (`onPerfEntry`) that will receive
  //   performance metrics if the user wants to track them.

  if (onPerfEntry && onPerfEntry instanceof Function) {
    // ↑ Only proceed if a valid function was provided.

    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      // ↑ Dynamically import the web-vitals library.
      //   This avoids loading performance tools unless needed.

      getCLS(onPerfEntry);  // Cumulative Layout Shift
      getFID(onPerfEntry);  // First Input Delay
      getFCP(onPerfEntry);  // First Contentful Paint
      getLCP(onPerfEntry);  // Largest Contentful Paint
      getTTFB(onPerfEntry); // Time To First Byte
      // ↑ Each metric is collected and passed into the callback.
    });
  }
};

export default reportWebVitals;
// ↑ Export function so index.js can call it (or ignore it).
