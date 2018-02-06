import { scansTypes } from '../constants';
import scansService from '../../services/scansService';

const getScansError = (bool, message) => ({
  type: scansTypes.GET_SCANS_ERROR,
  error: bool,
  message: message
});

const getScansLoading = bool => ({
  type: scansTypes.GET_SCANS_LOADING,
  loading: bool
});

const getScansSuccess = data => ({
  type: scansTypes.GET_SCANS_SUCCESS,
  data
});

const getScans = queryStr => {
  return function(dispatch) {
    dispatch(getScansLoading(true));

    return scansService
      .getScans('', queryStr)
      .then(success => {
        dispatch(getScansSuccess(success));
        dispatch(getScansLoading(false));
      })
      .catch(error => {
        dispatch(getScansError(true, error.message));
        dispatch(getScansLoading(false));
      });
  };
};

export { getScansError, getScansLoading, getScansSuccess, getScans };
