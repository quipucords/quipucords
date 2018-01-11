class ScansApi {
  static getScans() {
    return fetch('http://localhost:4000/api/v1/scans/')
      .then(response => {
        return response.json();
      })
      .catch(error => {
        return error;
      });
  }
}

export default ScansApi;
