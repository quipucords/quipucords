import * as types from '../constants/sourcesConstants';
import sourcesApi from '../../services/sourcesApi';

const sourcesError = bool => ({
  type: types.LOAD_SOURCES_ERROR,
  error: bool
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
    return sourcesApi
      .getSources()
      .then(success => {
        dispatch(sourcesSuccess(success));
      })
      .catch(() => dispatch(sourcesError(true)))
      .finally(() => dispatch(sourcesLoading(false)));
  };
};

export { sourcesError, sourcesLoading, sourcesSuccess, getSources };
