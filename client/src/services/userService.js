import axios from 'axios';
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

  static whoami() {
    return axios({
      method: 'get',
      url: `${process.env.REACT_APP_USER_SERVICE_CURRENT}`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER
    });
  }


  static logoutUser() {
    return axios({
      method: 'put',
      url: `${process.env.REACT_APP_USER_SERVICE_LOGOUT}`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER
    });
  }
}

export default UserService;
