import { aboutTypes } from '../constants';

const initialState = {
  show: false
};

export default function aboutReducer(state = initialState, action) {
  switch (action.type) {
    case aboutTypes.ABOUT_DIALOG_OPEN:
      return Object.assign({}, state, { show: true });

    case aboutTypes.ABOUT_DIALOG_CLOSE:
      return Object.assign({}, state, { show: false });

    default:
      return state;
  }
}
