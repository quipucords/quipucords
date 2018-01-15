import * as types from '../constants/sourcesConstants';
import sourcesApi from '../../services/sourcesApi';

const sourcesError = (bool, message) => ({
  type: types.LOAD_SOURCES_ERROR,
  error: bool,
  message: message
});

const sourcesLoading = bool => ({
  type: types.LOAD_SOURCES_LOADING,
  loading: bool
});

const sourcesSuccess = data => ({
  type: types.LOAD_SOURCES_SUCCESS,
  data
});

const getSources = () => {
  return function(dispatch) {
    dispatch(sourcesLoading(true));
    return sourcesApi
      .getSources()
      .then(success => {
        dispatch(sourcesSuccess(success));
      })
      .catch(error => {
        dispatch(sourcesError(true, error.message));
      })
      .finally(() => dispatch(sourcesLoading(false)));
  };
};

export { sourcesError, sourcesLoading, sourcesSuccess, getSources };
