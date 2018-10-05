import { reportsTypes } from '../constants';
import reportsService from '../../services/reportsService';

const getReportSummary = (id, query) => dispatch =>
  dispatch({
    type: reportsTypes.GET_REPORT,
    payload: reportsService.getReportSummary(id, query)
  });

const getReportSummaryCsv = (id, query) => dispatch =>
  dispatch({
    type: reportsTypes.GET_REPORT,
    payload: reportsService.getReportSummaryCsv(id, query)
  });

const getReportDetails = id => dispatch =>
  dispatch({
    type: reportsTypes.GET_REPORT,
    payload: reportsService.getReportDetails(id)
  });

const getReportDetailsCsv = id => dispatch =>
  dispatch({
    type: reportsTypes.GET_REPORT,
    payload: reportsService.getReportDetailsCsv(id)
  });

const getMergedScanReportSummaryCsv = id => dispatch =>
  dispatch({
    type: reportsTypes.GET_REPORT,
    payload: reportsService.getMergedScanReportSummaryCsv(id)
  });

const getMergedScanReportDetailsCsv = id => dispatch =>
  dispatch({
    type: reportsTypes.GET_REPORT,
    payload: reportsService.getMergedScanReportDetailsCsv(id)
  });

const mergeScanReports = data => dispatch =>
  dispatch({
    type: reportsTypes.GET_MERGE_REPORT,
    payload: reportsService.mergeScanReports(data)
  });

export {
  getReportSummary,
  getReportSummaryCsv,
  getReportDetails,
  getReportDetailsCsv,
  getMergedScanReportSummaryCsv,
  getMergedScanReportDetailsCsv,
  mergeScanReports
};
