import axios from 'axios';
import serviceConfig from './config';

const whoami = () =>
  axios(
    serviceConfig({
      method: 'get',
      url: process.env.REACT_APP_USER_SERVICE_CURRENT
    })
  );

const logoutUser = () =>
  axios(
    serviceConfig({
      method: 'put',
      url: process.env.REACT_APP_USER_SERVICE_LOGOUT
    })
  );

const userService = { whoami, logoutUser };

export { userService as default, userService, whoami, logoutUser };
