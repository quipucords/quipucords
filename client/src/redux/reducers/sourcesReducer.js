import * as types from '../constants/sourcesConstants';

const initialState = {
  error: false,
  errorMessage: '',
  loading: true,
  data: []
};

export default function sourcesReducer(state = initialState, action) {
  switch (action.type) {
    case types.LOAD_SOURCES_ERROR:
      return Object.assign({}, state, {
        error: action.error,
        errorMessage: action.message
      });

    case types.LOAD_SOURCES_LOADING:
      return Object.assign({}, state, { loading: action.loading });

    case types.LOAD_SOURCES_SUCCESS:
      return Object.assign({}, state, { data: action.data });

    default:
      return state;
  }
}
