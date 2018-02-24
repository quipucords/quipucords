import axios from 'axios';

class ScansService {
  static addScan(data = {}) {
    return axios({
      method: 'post',
      url: `${process.env.REACT_APP_SCANS_SERVICE}`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      data: data
    });
  }

  static startScan(id) {
    let apiPath = process.env.REACT_APP_SCANS_SERVICE_START.replace('{0}', id);

    return axios({
      method: 'post',
      url: apiPath,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER
    });
  }

  static cancelScan(id) {
    let apiPath = process.env.REACT_APP_SCANS_SERVICE_CANCEL.replace('{0}', id);

    return axios({
      method: 'put',
      url: apiPath,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER
    });
  }

  static getScan(id) {
    return this.getScans(id);
  }

  static getScans(id = '', query = {}) {
    return axios({
      url: `${process.env.REACT_APP_SCANS_SERVICE}${id}`,
      params: query
    });
  }

  static getScanResults(id) {
    let apiPath = process.env.REACT_APP_SCANS_SERVICE_RESULTS.replace('{0}', id);

    return axios({
      url: apiPath
    });
  }

  static getScanJobs(id) {
    let apiPath = process.env.REACT_APP_SCANS_SERVICE_JOBS.replace('{0}', id);
    return axios({
      url: apiPath
    });
  }

  static pauseScan(id) {
    let apiPath = process.env.REACT_APP_SCANS_SERVICE_PAUSE.replace('{0}', id);

    return axios({
      method: 'put',
      url: apiPath,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER
    });
  }

  static restartScan(id) {
    let apiPath = process.env.REACT_APP_SCANS_SERVICE_RESTART.replace('{0}', id);

    return axios({
      method: 'put',
      url: apiPath,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER
    });
  }
}

export default ScansService;
