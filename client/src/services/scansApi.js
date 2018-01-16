class ScansApi {
  static getScans() {
    return fetch(process.env.REACT_APP_SCANS_API).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(response.statusText);
      }
    });
  }
}

export default ScansApi;
