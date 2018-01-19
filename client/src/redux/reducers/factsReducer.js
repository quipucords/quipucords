import { factsTypes as types } from '../constants';

const initialState = {
  error: false,
  errorMessage: '',
  loading: true,
  data: {}
};

export default function factsReducer(state = initialState, action) {
  switch (action.type) {
    case types.ADD_FACTS_ERROR:
      return Object.assign({}, state, {
        error: action.error,
        errorMessage: action.message
      });

    case types.ADD_FACTS_LOADING:
      return Object.assign({}, state, { loading: action.loading });

    case types.ADD_FACTS_SUCCESS:
      return Object.assign({}, state, { data: action.data });

    default:
      return state;
  }
}
