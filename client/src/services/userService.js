import cookies from 'js-cookie';

class UserService {
  static authorizeUser() {
    // ToDo: ReEvaluate placement of this spoof for auth. Also consider using a helper function.
    if (process.env.REACT_APP_ENV === 'development') {
      cookies.set(process.env.REACT_APP_AUTH_TOKEN, 'spoof');

      console.warn('Warning: Loading spoof auth token.');
    }

    const token = cookies.get(process.env.REACT_APP_AUTH_TOKEN);

    return new Promise((resolve, reject) => {
      if (token) {
        return resolve({
          authToken: token
        });
      }

      throw new Error('User not authorized.');
    });
  }

  // ToDo: Replace randomized name generator
  static whoami() {
    const arr = ['admin', 'John Doe', 'Jane Doe'];

    return this.authorizeUser().then(
      response =>
        new Promise(resolve => {
          resolve({
            userName: arr[Math.floor(Math.random() * arr.length)]
          });
        })
    );
  }

  static logoutUser() {
    return this.whoami().then(
      response =>
        new Promise((resolve, reject) => {
          if (response && response.userName) {
            cookies.remove(process.env.REACT_APP_AUTH_TOKEN);

            return resolve({
              userName: response.userName
            });
          }

          throw new Error(
            `Error logging out, token doesn't exist for ${response.userName}.`
          );
        })
    );
  }
}

export default UserService;
