import axios from 'axios';
import cookies from 'js-cookie';
import { helpers } from '../common/helpers';

class UserService {
  static authorizeUser() {
    if (helpers.DEV_MODE) {
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
      url: process.env.REACT_APP_USER_SERVICE_CURRENT,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT
    });
  }

  static logoutUser() {
    return axios({
      method: 'put',
      url: process.env.REACT_APP_USER_SERVICE_LOGOUT,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT
    });
  }
}

export default UserService;
