class SourcesApi {
  static getSources() {
    return fetch('http://localhost:4000/api/v1/sources/')
      .then(response => {
        return response.json();
      })
      .catch(error => {
        return error;
      });
  }
}

export default SourcesApi;
