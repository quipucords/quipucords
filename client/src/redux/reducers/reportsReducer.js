import { reportsTypes } from '../constants';

const initialState = {
  error: false,
  errorMessage: '',
  loading: true,
  data: []
};

export default function reportsReducer(state = initialState, action) {
  switch (action.type) {
    case reportsTypes.GET_REPORTS_ERROR:
      return Object.assign({}, state, {
        error: action.error,
        errorMessage: action.message
      });

    case reportsTypes.GET_REPORTS_LOADING:
      return Object.assign({}, state, { loading: action.loading });

    case reportsTypes.GET_REPORTS_SUCCESS:
      return Object.assign({}, state, { data: action.data });

    default:
      return state;
  }
}
