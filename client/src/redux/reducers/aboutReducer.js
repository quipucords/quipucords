import * as types from '../constants/aboutConstants';

const initialState = {
  show: false
};

export default function aboutReducer(state = initialState, action) {
  switch (action.type) {
    case types.ABOUT_DIALOG_OPEN:
      return Object.assign({}, state, { show: true });

    case types.ABOUT_DIALOG_CLOSE:
      return Object.assign({}, state, { show: false });

    default:
      return state;
  }
}
