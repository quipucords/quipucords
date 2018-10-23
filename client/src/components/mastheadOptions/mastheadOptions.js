import React from 'react';
import PropTypes from 'prop-types';
import { Dropdown, Icon, MenuItem } from 'patternfly-react';
import helpers from '../../common/helpers';

const MastheadOptions = ({ user, logoutUser, showAboutModal }) => (
  <nav className="collapse navbar-collapse">
    <ul className="navbar-iconic nav navbar-nav navbar-right">
      <Dropdown componentClass="li" id="help">
        <Dropdown.Toggle useAnchor className="nav-item-iconic">
          <Icon type="pf" name="help" />
        </Dropdown.Toggle>
        <Dropdown.Menu>
          <MenuItem onClick={showAboutModal}>About</MenuItem>
        </Dropdown.Menu>
      </Dropdown>
      <Dropdown componentClass="li" id="user">
        <Dropdown.Toggle useAnchor className="nav-item-iconic">
          <Icon type="pf" name="user" /> {user.currentUser && user.currentUser.username}
        </Dropdown.Toggle>
        <Dropdown.Menu>
          <MenuItem onClick={logoutUser}>Log out</MenuItem>
        </Dropdown.Menu>
      </Dropdown>
    </ul>
  </nav>
);

MastheadOptions.propTypes = {
  user: PropTypes.object,
  logoutUser: PropTypes.func,
  showAboutModal: PropTypes.func
};

MastheadOptions.defaultProps = {
  user: {},
  logoutUser: helpers.noop,
  showAboutModal: helpers.noop
};

export { MastheadOptions as default, MastheadOptions };
