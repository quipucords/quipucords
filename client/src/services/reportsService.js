import axios from 'axios';
import serviceConfig from './config';
import helpers from '../common/helpers';

const getReportDetails = (id, params = {}) =>
  axios(
    serviceConfig(
      {
        url: process.env.REACT_APP_REPORTS_SERVICE_DETAILS.replace('{0}', id),
        params
      },
      false
    )
  );

const getReportDetailsCsv = id =>
  getReportDetails(id, { format: 'csv' }).then(
    success =>
      (helpers.TEST_MODE && success.data) ||
      helpers.downloadData(
        success.data,
        `report_${id}_details_${helpers.getTimeStampFromResults(success)}.csv`,
        'text/csv'
      )
  );

const getReportSummary = (id, params = {}) =>
  axios(
    serviceConfig(
      {
        url: process.env.REACT_APP_REPORTS_SERVICE_DEPLOYMENTS.replace('{0}', id),
        params
      },
      false
    )
  );

const getReportSummaryCsv = (id, params = {}) =>
  getReportSummary(id, Object.assign(params, { format: 'csv' })).then(
    success =>
      (helpers.TEST_MODE && success.data) ||
      helpers.downloadData(
        success.data,
        `report_${id}_summary_${helpers.getTimeStampFromResults(success)}.csv`,
        'text/csv'
      )
  );

const getMergedScanReportDetailsCsv = id =>
  getReportDetails(id, { format: 'csv' }).then(
    success =>
      (helpers.TEST_MODE && success.data) ||
      helpers.downloadData(
        success.data,
        `merged_report_details_${helpers.getTimeStampFromResults(success)}.csv`,
        'text/csv'
      )
  );

const getMergedScanReportSummaryCsv = id =>
  getReportSummary(id, { format: 'csv' }).then(
    success =>
      (helpers.TEST_MODE && success.data) ||
      helpers.downloadData(
        success.data,
        `merged_report_summary_${helpers.getTimeStampFromResults(success)}.csv`,
        'text/csv'
      )
  );

const mergeScanReports = (data = {}) =>
  axios(
    serviceConfig({
      method: 'put',
      url: process.env.REACT_APP_REPORTS_SERVICE_MERGE,
      data
    })
  );

const reportsService = {
  getReportDetails,
  getReportDetailsCsv,
  getReportSummary,
  getReportSummaryCsv,
  getMergedScanReportDetailsCsv,
  getMergedScanReportSummaryCsv,
  mergeScanReports
};

export {
  reportsService as default,
  reportsService,
  getReportDetails,
  getReportDetailsCsv,
  getReportSummary,
  getReportSummaryCsv,
  getMergedScanReportDetailsCsv,
  getMergedScanReportSummaryCsv,
  mergeScanReports
};
