import React from 'react';
import PropTypes from 'prop-types';
import { OverlayTrigger, Tooltip } from 'patternfly-react';

const SimpleTooltip = ({ children, tooltip, placement, trigger, delayShow, ...props }) => (
  <OverlayTrigger
    overlay={<Tooltip {...props}>{tooltip}</Tooltip>}
    placement={placement}
    trigger={trigger}
    delayShow={delayShow}
  >
    <span>{children}</span>
  </OverlayTrigger>
);

SimpleTooltip.propTypes = {
  children: PropTypes.node,
  tooltip: PropTypes.node,
  placement: PropTypes.string,
  trigger: PropTypes.array,
  delayShow: PropTypes.number
};

SimpleTooltip.defaultProps = {
  children: null,
  tooltip: null,
  placement: 'top',
  trigger: ['hover'],
  delayShow: 500
};

export { SimpleTooltip as default, SimpleTooltip };
