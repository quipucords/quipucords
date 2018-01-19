import jquery from 'jquery';

class ReportsService {
  static getReports(query = {}) {
    let queryStr = jquery.param(query);

    return fetch(`${process.env.REACT_APP_REPORTS_SERVICE}${queryStr}`).then(
      response => {
        if (response.ok) {
          return response.json();
        } else {
          throw new Error(response.statusText);
        }
      }
    );
  }
}

export default ReportsService;
