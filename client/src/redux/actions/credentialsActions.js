import * as types from '../constants/credentialsConstants';
import credentialsApi from '../../services/credentialsApi';

const credentialsError = (bool, message) => ({
  type: types.LOAD_CREDENTIALS_ERROR,
  error: bool,
  message: message
});

const credentialsLoading = bool => ({
  type: types.LOAD_CREDENTIALS_LOADING,
  loading: bool
});

const credentialsSuccess = data => ({
  type: types.LOAD_CREDENTIALS_SUCCESS,
  data
});

const getCredentials = () => {
  return function(dispatch) {
    dispatch(credentialsLoading(true));
    return credentialsApi
      .getCredentials()
      .then(success => {
        dispatch(credentialsSuccess(success));
      })
      .catch(error => {
        dispatch(credentialsError(true, error.message));
      })
      .finally(() => dispatch(credentialsLoading(false)));
  };
};

export {
  credentialsError,
  credentialsLoading,
  credentialsSuccess,
  getCredentials
};
