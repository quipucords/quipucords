import { reportsTypes } from '../constants';
import reportsService from '../../services/reportsService';

const getReportDeployments = (id, query) => dispatch => {
  return dispatch({
    type: reportsTypes.GET_REPORT_DEPLOYMENTS,
    payload: reportsService.getReportDeployments(id, query)
  });
};

const getReportDeploymentsCsv = (id, query) => dispatch => {
  return dispatch({
    type: reportsTypes.GET_REPORT_DEPLOYMENTS_CSV,
    payload: reportsService.getReportDeploymentsCsv(id, query)
  });
};

const getReportDetails = id => dispatch => {
  return dispatch({
    type: reportsTypes.GET_REPORT_DETAILS,
    payload: reportsService.getReportDetails(id)
  });
};

const getReportDetailsCsv = id => dispatch => {
  return dispatch({
    type: reportsTypes.GET_REPORT_DETAILS_CSV,
    payload: reportsService.getReportDetailsCsv(id)
  });
};

export { getReportDeployments, getReportDeploymentsCsv, getReportDetails, getReportDetailsCsv };
