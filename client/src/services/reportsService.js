import axios from 'axios';

class ReportsService {
  static getReports(query = {}) {
    return axios({
      url: `${process.env.REACT_APP_REPORTS_SERVICE}`,
      params: query
    });
  }
}

export default ReportsService;
