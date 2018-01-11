import * as types from '../constants/scansConstants';
import scansApi from '../../services/scansApi';

const loadScansSuccess = data => ({
  type: types.LOAD_SCANS_SUCCESS,
  data
});

const getScans = () => {
  return function(dispatch) {
    return scansApi
      .getScans()
      .then(success => {
        dispatch(loadScansSuccess(success));
      })
      .catch(error => {
        throw error;
      });
  };
};

export { loadScansSuccess, getScans };
