import * as types from '../constants/scansConstants';

const initialState = {
  error: false,
  errorMessage: '',
  loading: true,
  data: []
};

export default function scansReducer(state = initialState, action) {
  switch (action.type) {
    case types.LOAD_SCANS_ERROR:
      return Object.assign({}, state, {
        error: action.error,
        errorMessage: action.message
      });

    case types.LOAD_SCANS_LOADING:
      return Object.assign({}, state, { loading: action.loading });

    case types.LOAD_SCANS_SUCCESS:
      return Object.assign({}, state, { data: action.data });

    default:
      return state;
  }
}
