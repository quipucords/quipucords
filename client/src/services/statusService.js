import axios from 'axios';

class StatusService {
  static getStatus() {
    return axios({
      url: process.env.REACT_APP_STATUS_SERVICE,
      timeout: process.env.REACT_APP_AJAX_TIMEOUT
    });
  }
}

export default StatusService;
