import { confirmationModalTypes } from '../constants';

const initialState = {
  show: false,
  confirmTitle: 'Confirm',
  confirmHeading: null,
  confirmBody: null,
  confirmButtonText: 'Confirm'
};

export default function confirmationModalReducer(state = initialState, action) {
  switch (action.type) {
    case confirmationModalTypes.CONFIRMATION_MODAL_SHOW:
      return Object.assign({}, state, {
        show: true,
        title: action.title,
        heading: action.heading,
        body: action.body,
        confirmButtonText: action.confirmButtonText || 'Confirm',
        onConfirm: action.onConfirm,
        onCancel: action.onCancel
      });

    case confirmationModalTypes.CONFIRMATION_MODAL_HIDE:
      return Object.assign({}, state, {
        show: false
      });

    default:
      return state;
  }
}
