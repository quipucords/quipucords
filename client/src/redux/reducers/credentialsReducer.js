import * as types from '../constants/credentialsConstants';

const initialState = {
  data: []
};

export default function credentialsReducer(state = initialState, action) {
  switch (action.type) {
    case types.LOAD_CREDENTIALS_SUCCESS:
      return Object.assign({}, state, action.data);
    default:
      return state;
  }
}
