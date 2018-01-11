class CredentialsApi {
  static getCredentials() {
    return fetch('http://localhost:4000/api/v1/credentials/')
      .then(response => {
        return response.json();
      })
      .catch(error => {
        return error;
      });
  }
}

export default CredentialsApi;
