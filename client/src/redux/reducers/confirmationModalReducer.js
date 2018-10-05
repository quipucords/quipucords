import { confirmationModalTypes } from '../constants';

const initialState = {
  show: false,
  title: 'Confirm',
  heading: null,
  icon: null,
  body: null,
  confirmButtonText: 'Confirm',
  cancelButtonText: 'Cancel'
};

const confirmationModalReducer = (state = initialState, action) => {
  switch (action.type) {
    case confirmationModalTypes.CONFIRMATION_MODAL_SHOW:
      return Object.assign({}, state, {
        show: true,
        title: action.title,
        heading: action.heading,
        icon: action.icon,
        body: action.body,
        confirmButtonText: action.confirmButtonText || 'Confirm',
        cancelButtonText: action.cancelButtonText || 'Cancel',
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
};

confirmationModalReducer.initialState = initialState;

export { confirmationModalReducer as default, initialState, confirmationModalReducer };
