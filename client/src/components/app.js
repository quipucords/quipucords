import React from 'react';
import PropTypes from 'prop-types';

import { connect } from 'react-redux';
import { withRouter } from 'react-router';

import {
  AboutModal,
  Dropdown,
  Icon,
  MenuItem,
  VerticalNav
} from 'patternfly-react';

import { routes } from '../routes';
import Store from '../redux/store';

import Content from './content/content';
import ToastNotificationsList from './toastNotificationList/toastNotificatinsList';
import ConfirmationModal from './confirmationModal/confirmationModal';

import logo from '../styles/images/Red_Hat_logo.svg';
import productTitle from '../styles/images/title.svg';
import _ from 'lodash';
import { aboutTypes } from '../redux/constants';

class App extends React.Component {
  constructor() {
    super();
    this.menu = routes();
  }

  navigateTo(path) {
    const { history } = this.props;
    history.push(path);
  }

  renderMenuItems() {
    const { location } = this.props;

    return this.menu.map(item => {
      return (
        <VerticalNav.Item
          key={item.to}
          title={item.title}
          iconClass={item.iconClass}
          active={_.startsWith(location.pathname, item.to)}
          onClick={() => this.navigateTo(item.to)}
        />
      );
    });
  }

  showAboutModal() {
    Store.dispatch({ type: aboutTypes.ABOUT_DIALOG_OPEN });
  }

  render() {
    const { showAbout } = this.props;

    let closeAbout = () => Store.dispatch({ type: 'ABOUT_DIALOG_CLOSE' });

    return (
      <div className="layout-pf layout-pf-fixed">
        <VerticalNav>
          <VerticalNav.Masthead>
            <VerticalNav.Brand titleImg={productTitle} />
            <nav className="collapse navbar-collapse">
              <ul className="navbar-iconic nav navbar-nav navbar-right">
                <Dropdown componentClass="li" id="help">
                  <Dropdown.Toggle useAnchor className="nav-item-iconic">
                    <Icon type="pf" name="help" />
                  </Dropdown.Toggle>
                  <Dropdown.Menu>
                    <MenuItem>Help</MenuItem>
                    <MenuItem onClick={this.showAboutModal}>About</MenuItem>
                  </Dropdown.Menu>
                </Dropdown>
              </ul>
            </nav>
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
  showAbout: PropTypes.bool,
  location: PropTypes.object,
  history: PropTypes.shape({
    push: PropTypes.func.isRequired
  }).isRequired
};

function mapStateToProps(state, ownProps) {
  return {
    showAbout: state.about.show
  };
}

export default withRouter(connect(mapStateToProps)(App));
