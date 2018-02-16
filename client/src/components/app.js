import React from 'react';
import PropTypes from 'prop-types';

import { connect } from 'react-redux';
import { withRouter } from 'react-router';

import {
  AboutModal,
  Alert,
  EmptyState,
  Modal,
  VerticalNav
} from 'patternfly-react';

import { routes } from '../routes';
import Store from '../redux/store';

import Content from './content/content';
import ToastNotificationsList from './toastNotificationList/toastNotificatinsList';
import ConfirmationModal from './confirmationModal/confirmationModal';
import MastheadOptions from './mastheadOptions/mastheadOptions';

import logo from '../styles/images/Red_Hat_logo.svg';
import productTitle from '../styles/images/title.svg';
import _ from 'lodash';
import { aboutTypes } from '../redux/constants';
import { authorizeUser } from '../redux/actions/userActions';

class App extends React.Component {
  constructor() {
    super();
    this.menu = routes();
  }

  componentDidMount() {
    this.props.authorizeUser();
  }

  navigateTo(path) {
    const { history } = this.props;
    history.push(path);
  }

  renderMenuItems() {
    const { location } = this.props;

    let activeItem = this.menu.find(item =>
      _.startsWith(location.pathname, item.to)
    );

    return this.menu.map(item => {
      return (
        <VerticalNav.Item
          key={item.to}
          title={item.title}
          iconClass={item.iconClass}
          active={item === activeItem || (!activeItem && item.redirect)}
          onClick={() => this.navigateTo(item.to)}
        />
      );
    });
  }

  showAboutModal() {
    Store.dispatch({ type: aboutTypes.ABOUT_DIALOG_OPEN });
  }

  render() {
    const { showAbout, session } = this.props;

    let closeAbout = () =>
      Store.dispatch({ type: aboutTypes.ABOUT_DIALOG_CLOSE });

    if (session.error) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Login error: {session.errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }

    if (session.pending || !session.fulfilled) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Logging in...</div>
          </Modal.Body>
        </Modal>
      );
    }

    if (!session.loggedIn) {
      setTimeout(() => {
        window.location = '/login';
      }, 5000);

      return (
        <div className="layout-pf layout-pf-fixed hidden-nav-menu">
          <VerticalNav persistentSecondary={false}>
            <VerticalNav.Masthead>
              <VerticalNav.Brand titleImg={productTitle} />
            </VerticalNav.Masthead>
          </VerticalNav>
          <div className="container-pf-nav-pf-vertical">
            <EmptyState className="full-page-blank-slate">
              <Alert type="error">
                <span>
                  You have been logged out: redirecting to the login page.
                </span>
              </Alert>
            </EmptyState>
          </div>
        </div>
      );
    }

    return (
      <div className="layout-pf layout-pf-fixed">
        <VerticalNav persistentSecondary={false}>
          <VerticalNav.Masthead>
            <VerticalNav.Brand titleImg={productTitle} />
            <MastheadOptions />
          </VerticalNav.Masthead>
          {this.renderMenuItems()}
        </VerticalNav>
        <div className="container-pf-nav-pf-vertical">
          <Content />
        </div>
        <AboutModal
          key="aboutModal"
          show={showAbout}
          onHide={closeAbout}
          productTitle={
            <img src={productTitle} alt="Red Hat Entitlements Reporting" />
          }
          logo={logo}
          altLogo="RH ER"
          trademarkText="Copyright (c) 2018 Red Hat Inc."
        >
          <AboutModal.Versions>
            <AboutModal.VersionItem label="Label" versionText="Version" />
            <AboutModal.VersionItem label="Label" versionText="Version" />
            <AboutModal.VersionItem label="Label" versionText="Version" />
            <AboutModal.VersionItem label="Label" versionText="Version" />
            <AboutModal.VersionItem label="Label" versionText="Version" />
            <AboutModal.VersionItem label="Label" versionText="Version" />
            <AboutModal.VersionItem label="Label" versionText="Version" />
          </AboutModal.Versions>
        </AboutModal>
        <ToastNotificationsList key="toastList" />
        <ConfirmationModal key="confirmationModal" />
      </div>
    );
  }
}

App.propTypes = {
  authorizeUser: PropTypes.func,
  session: PropTypes.object,
  showAbout: PropTypes.bool,
  location: PropTypes.object,
  history: PropTypes.shape({
    push: PropTypes.func.isRequired
  }).isRequired
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  authorizeUser: () => dispatch(authorizeUser())
});

function mapStateToProps(state, ownProps) {
  return {
    session: state.user.session,
    showAbout: state.about.show
  };
}

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(App));
