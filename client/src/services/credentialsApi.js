class CredentialsApi {
  static getCredentials() {
    return fetch(process.env.REACT_APP_CREDENTIALS_API).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(response.statusText);
      }
    });
  }
}

export default CredentialsApi;
