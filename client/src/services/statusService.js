import axios from 'axios';

class StatusService {
  static getStatus() {
    return axios({
      method: 'get',
      url: process.env.REACT_APP_STATUS_SERVICE
    });
  }
}

export default StatusService;
