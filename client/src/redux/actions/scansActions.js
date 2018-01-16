import * as types from '../constants/scansConstants';
import scansApi from '../../services/scansApi';

const scansError = (bool, message) => ({
  type: types.LOAD_SCANS_ERROR,
  error: bool,
  message: message
});

const scansLoading = bool => ({
  type: types.LOAD_SCANS_LOADING,
  loading: bool
});

const scansSuccess = data => ({
  type: types.LOAD_SCANS_SUCCESS,
  data
});

const getScans = () => {
  return function(dispatch) {
    dispatch(scansLoading(true));
    return scansApi
      .getScans()
      .then(success => {
        dispatch(scansSuccess(success));
      })
      .catch(error => {
        dispatch(scansError(true, error.message));
      })
      .finally(() => dispatch(scansLoading(false)));
  };
};

export { scansError, scansLoading, scansSuccess, getScans };
