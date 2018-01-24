import { reportsTypes } from '../constants';
import reportsService from '../../services/reportsService';

const getReportsError = (bool, message) => ({
  type: reportsTypes.GET_REPORTS_ERROR,
  error: bool,
  message: message
});

const getReportsLoading = bool => ({
  type: reportsTypes.GET_REPORTS_LOADING,
  loading: bool
});

const getReportsSuccess = data => ({
  type: reportsTypes.GET_REPORTS_SUCCESS,
  data
});

const getReports = () => {
  return function(dispatch) {
    dispatch(getReportsLoading(true));
    return reportsService
      .getReports()
      .then(success => {
        dispatch(getReportsSuccess(success));
        dispatch(getReportsLoading(false));
      })
      .catch(error => {
        dispatch(getReportsError(true, error.message));
        dispatch(getReportsLoading(false));
      });
  };
};

export { getReportsError, getReportsLoading, getReportsSuccess, getReports };
