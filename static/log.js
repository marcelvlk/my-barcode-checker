function startLogPolling(jobId) {
  const logBox = document.getElementById("logbox");

  async function fetchLog() {
    const res = await fetch("/log/" + jobId);
    if (res.ok) {
      const text = await res.text();
      logBox.textContent = text;
      logBox.scrollTop = logBox.scrollHeight;

      if (text.includes("✅ Scraping complete!")) {
        window.location.href = "/result/" + jobId;
      } else {
        setTimeout(fetchLog, 2000);
      }
    }
  }

  fetchLog();
}
