import * as types from '../constants/credentialsConstants';
import credentialsApi from '../../services/credentialsApi';

const loadCredentialsSuccess = data => ({
  type: types.LOAD_CREDENTIALS_SUCCESS,
  data
});

const getCredentials = () => {
  return function(dispatch) {
    return credentialsApi
      .getCredentials()
      .then(success => {
        dispatch(loadCredentialsSuccess(success));
      })
      .catch(error => {
        throw error;
      });
  };
};

export { loadCredentialsSuccess, getCredentials };
