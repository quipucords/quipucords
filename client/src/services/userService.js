import cookies from 'js-cookie';

class UserService {
  static authorizeUser() {
    const token = cookies.get('csrftoken');

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
          const token = cookies.get('csrftoken');

          if (token) {
            cookies.remove('csrftoken');

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
