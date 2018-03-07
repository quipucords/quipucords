import axios from 'axios';

class StatusService {
  static getStatus() {
    return axios({
      method: 'get',
      url: process.env.REACT_APP_STATUS_SERVICE,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER
    });
  }
}

export default StatusService;
