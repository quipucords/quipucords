import { credentialsTypes as types } from '../constants';

const initialState = {
  error: false,
  errorMessage: '',
  loading: true,
  data: []
};

export default function credentialsReducer(state = initialState, action) {
  switch (action.type) {
    case types.GET_CREDENTIALS_ERROR:
      return Object.assign({}, state, {
        error: action.error,
        errorMessage: action.message
      });

    case types.GET_CREDENTIALS_LOADING:
      return Object.assign({}, state, { loading: action.loading });

    case types.GET_CREDENTIALS_SUCCESS:
      return Object.assign({}, state, { data: action.data });

    default:
      return state;
  }
}
