import _ from 'lodash';
import axios from 'axios';
import moment from 'moment';

class ReportsService {
  static getTimeStampFromResults(results) {
    return moment(_.get(results, 'headers.date', Date.now())).format('YYYYMMDD_HHmmss');
  }

  static downloadCSV(data = '', fileName = 'report.csv') {
    return new Promise((resolve, reject) => {
      try {
        const blob = new Blob([data], { type: 'text/csv' });

        if (window.navigator && window.navigator.msSaveBlob) {
          window.navigator.msSaveBlob(blob, fileName);
          resolve({ fileName: fileName, data: data });
        } else {
          let anchorTag = window.document.createElement('a');

          anchorTag.href = window.URL.createObjectURL(blob);
          anchorTag.style.display = 'none';
          anchorTag.download = fileName;

          window.document.body.appendChild(anchorTag);

          anchorTag.click();

          setTimeout(() => {
            window.document.body.removeChild(anchorTag);
            window.URL.revokeObjectURL(blob);
            resolve({ fileName: fileName, data: data });
          }, 250);
        }
      } catch (error) {
        reject(error);
      }
    });
  }

  static getReportDetails(id, query = {}) {
    let apiPath = process.env.REACT_APP_REPORTS_SERVICE_DETAILS.replace('{0}', id);

    return axios({
      url: apiPath,
      params: query
    });
  }

  static getReportDetailsCsv(id) {
    return this.getReportDetails(id, { format: 'csv' }).then(success => {
      return this.downloadCSV(success.data, `report_${id}_details_${this.getTimeStampFromResults(success)}.csv`);
    });
  }

  static getReportSummary(id, query = {}) {
    let apiPath = process.env.REACT_APP_REPORTS_SERVICE_DEPLOYMENTS.replace('{0}', id);

    return axios({
      url: apiPath,
      params: query
    });
  }

  static getReportSummaryCsv(id, query = {}) {
    return this.getReportSummary(id, Object.assign(query, { format: 'csv' })).then(success => {
      return this.downloadCSV(success.data, `report_${id}_summary_${this.getTimeStampFromResults(success)}.csv`);
    });
  }

  static getMergedScanReportDetailsCsv(id) {
    return this.getReportDetails(id, { format: 'csv' }).then(success => {
      return this.downloadCSV(success.data, `merged_report_details_${this.getTimeStampFromResults(success)}.csv`);
    });
  }
  static getMergedScanReporSummaryCsv(id) {
    return this.getReportSummary(id, { format: 'csv' }).then(success => {
      return this.downloadCSV(success.data, `merged_report_summary_${this.getTimeStampFromResults(success)}.csv`);
    });
  }
}

export default ReportsService;
