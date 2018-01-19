import { sourcesTypes as types } from '../constants';

const initialState = {
  error: false,
  errorMessage: '',
  loading: true,
  data: []
};

export default function sourcesReducer(state = initialState, action) {
  switch (action.type) {
    case types.GET_SOURCES_ERROR:
      return Object.assign({}, state, {
        error: action.error,
        errorMessage: action.message
      });

    case types.GET_SOURCES_LOADING:
      return Object.assign({}, state, { loading: action.loading });

    case types.GET_SOURCES_SUCCESS:
      return Object.assign({}, state, { data: action.data });

    default:
      return state;
  }
}
