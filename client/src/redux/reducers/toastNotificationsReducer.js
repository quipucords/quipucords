import { toastNotificationTypes } from '../constants';

const initialState = {
  toasts: [],
  paused: false,
  displayedToasts: 0
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

      return {
        ...state,
        ...{
          toasts: [...state.toasts, newToast],
          displayedToasts: state.displayedToasts + 1
        }
      };

    case toastNotificationTypes.TOAST_REMOVE:
      const displayedToast = state.toasts.find(toast => !toast.removed);
      let updatedToasts = [];

      if (displayedToast) {
        updatedToasts = [...state.toasts];
        updatedToasts[state.toasts.indexOf(action.toast)].removed = true;
      }

      return {
        ...state,
        ...{
          toasts: updatedToasts
        }
      };

    case toastNotificationTypes.TOAST_PAUSE:
      return {
        ...state,
        ...{
          paused: true
        }
      };

    case toastNotificationTypes.TOAST_RESUME:
      return {
        ...state,
        ...{
          paused: false
        }
      };

    default:
      return state;
  }
};

toastNotificationsReducer.initialState = initialState;

export { toastNotificationsReducer as default, initialState, toastNotificationsReducer };
