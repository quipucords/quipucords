import { toastNotificationTypes } from '../constants';

const initialState = {
  toasts: [],
  paused: false
};

const toastNotificationsReducer = (state = initialState, action) => {
  switch (action.type) {
    case toastNotificationTypes.TOAST_ADD:
      const newToast = {
        header: action.header,
        message: action.message,
        alertType: action.alertType,
        persistent: action.persistent
      };

      return Object.assign({}, state, {
        toasts: [...state.toasts, newToast],
        displayedToasts: state.displayedToasts + 1
      });

    case toastNotificationTypes.TOAST_REMOVE:
      const index = state.toasts.indexOf(action.toast);
      action.toast.removed = true;

      const displayedToast = state.toasts.find(toast => !toast.removed);

      if (!displayedToast) {
        return Object.assign({}, state, { toasts: [] });
      }

      return Object.assign({}, state, {
        toasts: [...state.toasts.slice(0, index), action.toast, ...state.toasts.slice(index + 1)]
      });

    case toastNotificationTypes.TOAST_PAUSE:
      return Object.assign({}, state, { paused: true });

    case toastNotificationTypes.TOAST_RESUME:
      return Object.assign({}, state, { paused: false });

    default:
      return state;
  }
};

toastNotificationsReducer.initialState = initialState;

export { toastNotificationsReducer as default, initialState, toastNotificationsReducer };
